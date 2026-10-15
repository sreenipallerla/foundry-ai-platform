// Resource-group scoped. One RG per environment: rg-fai-dev, rg-fai-qa, rg-fai-prod.
// NOTE: written without deploying. API versions and Foundry project resources change; check `az bicep` warnings.
targetScope = 'resourceGroup'

@allowed(['dev', 'qa', 'prod'])
param env string
param location string = resourceGroup().location
param searchLocation string = location
param prefix string = 'fai'
param chatModel string = 'gpt-4.1-mini'
param chatModelVersion string = '2025-04-14'
param embedModel string = 'text-embedding-3-small'
param aksNodeCount int = env == 'prod' ? 3 : 1

var suffix = uniqueString(resourceGroup().id)
var name = '${prefix}-${env}'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${name}'
  location: location
  properties: { sku: { name: 'PerGB2018' }, retentionInDays: 30 }
}

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${name}'
  location: location
  kind: 'web'
  properties: { Application_Type: 'web', WorkspaceResourceId: logs.id }
}

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${prefix}-${env}-${take(suffix, 6)}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
  }
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'acr${prefix}${env}${take(suffix, 6)}'
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}

// Azure AI Foundry resource (kind AIServices) hosts the model deployments.
resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: 'ais-${name}-${take(suffix, 6)}'
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    customSubDomainName: 'ais-${name}-${take(suffix, 6)}'
    publicNetworkAccess: 'Enabled'
    allowProjectManagement: true
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: foundry
  name: 'proj-${name}'
  dependsOn: [embed]
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {}
}

resource chat 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundry
  name: chatModel
  sku: { name: 'GlobalStandard', capacity: 30 }
  properties: { model: { format: 'OpenAI', name: chatModel, version: chatModelVersion } }
}

resource embed 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: foundry
  name: embedModel
  dependsOn: [chat]
  sku: { name: 'GlobalStandard', capacity: 30 }
  properties: { model: { format: 'OpenAI', name: embedModel, version: '1' } }
}

resource search 'Microsoft.Search/searchServices@2023-11-01' = {
  name: 'srch-${name}-${take(suffix, 6)}'
  location: searchLocation
  sku: { name: 'basic' }
  properties: { replicaCount: 1, partitionCount: 1, authOptions: { aadOrApiKey: { aadAuthFailureMode: 'http401WithBearerChallenge' } } }
}

resource aks 'Microsoft.ContainerService/managedClusters@2024-05-01' = {
  name: 'aks-${name}'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    dnsPrefix: 'aks-${name}'
    oidcIssuerProfile: { enabled: true }
    securityProfile: { workloadIdentity: { enabled: true } }
    agentPoolProfiles: [
      { name: 'system', count: aksNodeCount, vmSize: 'Standard_D2s_v5', mode: 'System', osType: 'Linux' }
    ]
    addonProfiles: {
      omsagent: { enabled: true, config: { logAnalyticsWorkspaceResourceID: logs.id } }
    }
  }
}

// AKS kubelet may pull from ACR (AcrPull).
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, aks.id, 'acrpull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: aks.properties.identityProfile.kubeletidentity.objectId
    principalType: 'ServicePrincipal'
  }
}

output foundryEndpoint string = foundry.properties.endpoint
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output acrName string = acr.name
output aksName string = aks.name
output keyVaultName string = kv.name
output appInsightsConnection string = appi.properties.ConnectionString
