"""Validate credentials over stdin; return only the detected username."""
import json,sys
try:
    credentials=json.loads(sys.stdin.read())
    from kagglesdk.kaggle_client import KaggleClient
    token=credentials.get('api_token')
    with KaggleClient(username=credentials.get('username') or None,password=credentials.get('key'),api_token=token) as client:
        username=credentials.get('username','')
        if token:
            from kagglesdk.security.types.oauth_service import IntrospectTokenRequest
            request=IntrospectTokenRequest();request.token=token
            info=client.security.oauth_client.introspect_token(request)
            if not info.active or not info.username:raise ValueError('Token inactivo')
            username=info.username
        if not username:raise ValueError('El JSON legacy debe incluir username')
        from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest
        request=ApiListKernelsRequest();request.user=username;request.page_size=1
        client.kernels.kernels_api_client.list_kernels(request)
    print(json.dumps({'ok':True,'username':username}))
except Exception as error:
    print(json.dumps({'ok':False,'error':type(error).__name__}));sys.exit(1)
