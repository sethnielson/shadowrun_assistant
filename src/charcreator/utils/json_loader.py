import json

# Registry: type string -> factory
_TYPE_REGISTRY = {}

def register_json_type(type_name):
    def wrapper(cls):
        _TYPE_REGISTRY[type_name] = cls
        return cls
    return wrapper
    
def obj_list_to_dict(obj_list):
    d = {}
    for item in obj_list:
        if not isinstance(item, JsonObject):
            raise Exception("Data lists must contain JsonObjects")
        if item._key in d:
            raise Exception("Each item in a data list must have a unique keye")
        d[item._key] = item
    return d

class JsonObject:
    def __init__(self, **kargs):
        self._key = kargs["key"]
        self._name = kargs["name"]
        self._attrs = {k:kargs[k] for k in kargs if k not in ["__type__", "key", "name", "namespace"]}
        if "data" in kargs:
            self._static = obj_list_to_dict(kargs["data"].get("static",[]))
            self._dynamic = obj_list_to_dict(kargs["data"].get("dynamic",[]))
        else:
            self._static = {}
            self._dynamic = {}
        
    def attrs(self):
        return self._attrs.keys()
    
    def get_attr(self, k):
        return self._attrs.get(k, None)
        
    def keys(self):
        keys = [self._key]
        for key in self._static:
            if isinstance(self._static[key], JsonObject):
                for subkey in self._static[key].keys():
                    keys.append(self._key+subkey)
            else:
                keys.append(self._key+key)
        return keys
        
    def get(self, key):
        key_parts = key.split(".")
        next_key = key_parts[0]
        rem_key = ".".join(key_parts[1:])
        if next_key in self._static:
            return self._static[next_key].get(rem_key)
        elif next_key in self._dynamic:
            return self._dynamic[next_key].get(rem_key)
        return None
        
    def merge(self, obj):
        if self._key != obj._key: raise Exception(f"Cannot merge objects with different keys - {self._key} v {obj._key}")
        if self._name != obj._name: raise Exception(f"Cannot merge objects with different names - {self._name} v {obj._name}")
        for (my_list, obj_list) in [(self._static, obj._static), (obj._static, obj._dynamic)]:
            for list_obj in obj_list:
                #print(self._key, "merge",list_obj, obj_list[list_obj])
                if list_obj not in my_list:
                    my_list[list_obj] = obj_list[list_obj]
                else:
                    my_list[list_obj].merge(obj_list[list_obj])
        
class Namespace(JsonObject):
    def __init__(self, **kargs):
        self._namespace_type = (
            "defines" in kargs["namespace"] and "defines" or
            "extends" in kargs["namespace"] and "extends" or
            "unknown"
            )
        self._namespace = kargs["namespace"][self._namespace_type]
        kargs["key"] = self._namespace
        kargs["name"] = "Namespace: "+self._namespace
        super().__init__(**kargs)
        
    def merge(self, namespace):
        if not isinstance(namespace, Namespace): raise Exception(f"Cannot merge namespace {self._namespace} with non-namesapce {namespace._key}")
        if self._namespace_type != "defines": raise Exception("Can only merge into namespace definition")
        if namespace._namespace_type != "extends": raise Exception("Can only merge namespace extensions")
        super().merge(namespace)

# Generic hook
def custom_object_hook(d):
    if "namespace" in d and "schema_version" in d:
        cls = Namespace
    elif "__type__" in d:
        t = d["__type__"]
        if t and t in _TYPE_REGISTRY:
            cls = _TYPE_REGISTRY[t]
        else:
            raise Exception(f"Unknown type {t}")
    elif "key" in d and "name" in d:
        cls = JsonObject
    else:
        return d
    
    kwargs = {k: v for k, v in d.items() if k != "__type__"}
    return cls(**kwargs)
    
class Namespaces:
    def __init__(self):
        self._namespaces = {}
        self._waiting_merges = {}
        
    def load_json(self, json_doc):
        item = json.loads(json_doc, object_hook=custom_object_hook)
        
        if not isinstance(item, Namespace):
            raise Exception("All top-level json documents must be namesapces")
        if item._key in self._namespaces:
            self._namespaces[item._namespace].merge(item)
        elif item._namespace_type == "extends":
            self._waiting_merges[item._namespace] = self._waiting_merges.get(item._namespace, []) + [item]
        else:
            self._namespaces[item._namespace] = item
            if item._namespace in self._waiting_merges:
                for m in self._waiting_merges[item._namespace]:
                    item.merge(m)
                del self._waiting_merges[item._namespace]
                
if __name__=="__main__":
    import sys, os
    folder = sys.argv[1]
    n = Namespaces()
    for fname in os.listdir(folder):
        if not fname.endswith(".json"): continue
        print("Loading", fname)
        fpath = os.path.join(folder, fname)
        with open(fpath) as f:
            n.load_json(f.read())
    print(f"unmerged namespaces: {list(n._waiting_merges.keys())}")
    for namespace in n._namespaces:
        print(n._namespaces[namespace].keys())
    