from .type_icon_map import TYPE_ICON_MAP
from .account_icon_map import ACCOUNT_ICON_MAP

def type_icon_map(request):
    return {"type_icon_map": TYPE_ICON_MAP}

def account_icon_map(request):
    return {"account_icon_map": ACCOUNT_ICON_MAP}
