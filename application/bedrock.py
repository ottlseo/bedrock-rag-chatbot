import os, sys, boto3
from variables import KNOWLEDGE_BASE_ID, MODEL_ARN, REGION

bedrock_agent_runtime_client = boto3.client("bedrock-agent-runtime", region_name=REGION)

def query(question):
    response = bedrock_agent_runtime_client.retrieve_and_generate(
        input={
            'text': question
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': MODEL_ARN,
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'overrideSearchType': 'HYBRID'
                    }
                }
            }
        },
    )
    return response['output']['text']
