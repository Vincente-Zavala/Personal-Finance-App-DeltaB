from .typeiconmap import TYPEICONMAP
from .accounticonmap import ACCOUNTICONMAP

def typeiconmap(request):
    return {"typeiconmap": TYPEICONMAP}

def accounticonmap(request):
    return {"accounticonmap": ACCOUNTICONMAP}
