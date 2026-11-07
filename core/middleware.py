class NoStoreDynamicPagesMiddleware:
    """Las respuestas dinámicas pueden contener sesión, CSRF o información privada."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        public_files = {'/offline/', '/manifest.webmanifest', '/service-worker.js'}
        if not request.path.startswith('/static/') and request.path not in public_files:
            response['Cache-Control'] = 'no-store, private'
        return response
