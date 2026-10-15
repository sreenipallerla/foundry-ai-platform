"""Submit a supervised fine-tuning job to Azure OpenAI. Needs a fine-tunable base model in your region and
enough training rows (the service enforces a minimum; the sample pairs.csv is only for practising the flow).
Usage: python finetune/submit_job.py gpt-4o-mini-2024-07-18"""
import os
import sys
import time

from openai import AzureOpenAI

base = sys.argv[1] if len(sys.argv) > 1 else "gpt-4o-mini-2024-07-18"
client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"], api_key=os.environ["AZURE_OPENAI_API_KEY"],
                     api_version="2024-10-21")
train = client.files.create(file=open("finetune/train.jsonl", "rb"), purpose="fine-tune")
val = client.files.create(file=open("finetune/validation.jsonl", "rb"), purpose="fine-tune")
job = client.fine_tuning.jobs.create(model=base, training_file=train.id, validation_file=val.id,
                                     hyperparameters={"n_epochs": 3})
print("job", job.id)
while job.status not in {"succeeded", "failed", "cancelled"}:
    time.sleep(30)
    job = client.fine_tuning.jobs.retrieve(job.id)
    print(job.status)
print("fine_tuned_model:", job.fine_tuned_model)
print("Next: deploy it in Foundry (Models + endpoints), then set CHAT_DEPLOYMENT to the new deployment name.")
