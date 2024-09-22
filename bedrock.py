import os, sys, boto3
from variables import KNOWLEDGE_BASE_ID

# bedrock_agent_client = boto3.client('bedrock-agent', region_name=region_name)
bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime", region_name="us-west-2")
model_arn = "anthropic.claude-3-sonnet-20240229-v1:0"

def query(question):
    response = bedrock_agent_runtime_client.retrieve_and_generate(
        input={
            'text': question
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': model_arn,
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'overrideSearchType': 'HYBRID'
                    }
                }
            }
        },
    )
    return response['output']['text']
