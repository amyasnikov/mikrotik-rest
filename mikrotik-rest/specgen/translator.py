

class Translate:

    _mtik = {
        'post' : 'add',
        'get' : 'print',
        'patch' : 'set',
        'delete' : 'remove'
    }

    _http = {v:k for k,v in _mtik.items()}


    @staticmethod
    def to_http(mikrotik_method):
        return Translate._http[mikrotik_method]


    @staticmethod
    def to_mtik(http_method):
        return Translate._mtik[http_method]