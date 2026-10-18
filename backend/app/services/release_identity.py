"""Deployment-declared build identity, never an attestation or host-path probe."""
import os
import re


def release_identity():
    value=os.environ.get('CHRONOSGRAPH_BUILD_COMMIT','')
    commit=value if re.fullmatch(r'[0-9a-f]{40}',value) else None
    return {'application_commit':commit,'status':'DECLARED' if commit else 'UNRECORDED',
            'basis':'DEPLOYMENT_ENVIRONMENT_DECLARATION_NOT_CRYPTOGRAPHIC_ATTESTATION',
            'model_calls':0}
