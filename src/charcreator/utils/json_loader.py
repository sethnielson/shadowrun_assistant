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
            raise Exception(f"Data lists must contain JsonObjects: {item}")
        if not item._key.startswith("."):
            raise Exception(f"Currently,only relative keys (starting with '.') are supported, got {item._key}")
        storage_key = item._key[1:] # remove relative '.'
        if storage_key in d:
            raise Exception(f"Each item in in data list must have a unique keye: {storage_key}")
        d[storage_key] = item 
    return d

class JsonObject:
    def __init__(self, **kargs):
        self._key = kargs["key"]
        self._name = kargs["name"]
        self._attrs = {k:kargs[k] for k in kargs if (k not in ["key", "name", "namespace"] and not k.startswith("__"))}
        if "data" in kargs:
            self._static = obj_list_to_dict(kargs["data"].get("static",[]))
            self._dynamic = obj_list_to_dict(kargs["data"].get("dynamic",[]))
        else:
            self._static = {}
            self._dynamic = {}
        if "list" in kargs:
            self._list_contents = obj_list_to_dict(kargs["list"])
        else:
            self._list_contents = {}
        
    def attrs(self):
        return self._attrs.keys()
    
    def get_attr(self, k):
        return self._attrs.get(k, None)
        
    def keys(self):
        keys = [self._key]
        for obj_list in [self._static, self._dynamic, self._list_contents]:
            for key in obj_list:
                if isinstance(obj_list[key], JsonObject):
                    for subkey in obj_list[key].keys():
                        keys.append(self._key+subkey)
                else:
                    raise Exception(f"Attempt to add {key} which does not refer to JsonObj")
        return keys
        
    def get(self, key):
        if key.startswith(self._key):
            key = key[len(self._key)+1:] # remove self._key + "."
        elif key.startswith('.'):
            key = key[1:] # remove "."
        else:
            raise Exception(f"Lookup on {self._key} must start with that prefix or '.': got f{key}")
        key_parts = key.split(".")
        next_key = key_parts[0]
        rem_key = ".".join(key_parts[1:])
        for obj_list in [self._static, self._dynamic, self._list_contents]:
            if next_key in obj_list:
                if not rem_key:
                    return obj_list[next_key]
                return obj_list[next_key].get("."+rem_key) # JsonObject expects relative "." at start
        return None
        
    def __str__(self):
        s = self.__repr__()
        for attr in self._attrs:
            if attr in ["key", "name", "namespace", "list", "data"]: continue
            s += f"\n\t{attr}: {self._attrs[attr]}"
        for obj_list, list_name in [(self._static, "Static Data"), (self._dynamic, "Dynamic Data"), (self._list_contents, "List Contents")]:
            if obj_list:
                s += f"\n{list_name}"
                for k in obj_list:
                    s+= f"\n\t{repr(obj_list[k])}"
        return s
        
    def __repr__(self):
        return f"JsonObject({self._key}: {self._name})"
        
    def merge(self, obj):
        if self._key != obj._key: raise Exception(f"Cannot merge objects with different keys - {self._key} v {obj._key}")
        if self._name != obj._name: raise Exception(f"Cannot merge objects with different names - {self._name} v {obj._name}")
        for (my_list, obj_list) in [(self._static, obj._static), (self._dynamic, obj._dynamic), (self._list_contents, obj._list_contents)]:
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
            "implicit" in kargs["namespace"] and "implicit" or 
            "unknown"
            )
        self._namespace = kargs["namespace"][self._namespace_type]
            
        if "." in self._namespace:
            kargs["key"] = "."+self._namespace.split(".")[-1]
            self._parent_ref = ".".join(self._namespace.split(".")[:-1])
        else:
            kargs["key"] = self._namespace
            self._parent_ref = ""
        kargs["name"] = "Namespace: "+self._namespace
        super().__init__(**kargs)
        
    def merge(self, namespace):
        print("merge into", self._namespace_type, self._namespace)
        if not isinstance(namespace, Namespace): 
            raise Exception(f"Cannot merge namespace {self._namespace} with non-namesapce {namespace._key}")
        if self._namespace_type not in ["defines", "implicit"]: 
            raise Exception("Can only merge into namespace definition or implicit namespace")
        if self._namespace_type == "defines" and namespace._namespace_type not in ["extends", "implicit"]: 
            raise Exception(f"Can only merge namespace extensions or implicit namespaces into definitions. Got {namespace._namespace_type} {namespace._namespace}.")
        if self._namespace_type == "implicit" and namespace._namespace_type not in ["implicit"]:
            raise Exception("Can only merge implicit namespaces into implicit namespaces")
        super().merge(namespace)
        print("done with", self._key, self._namespace_type, self._namespace)

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
        if item._namespace in self._namespaces:
            self._namespaces[item._namespace].merge(item)
        elif item._namespace_type != "defines":
            self._waiting_merges[item._namespace] = self._waiting_merges.get(item._namespace, []) + [item]
        else:
            self._namespaces[item._namespace] = item
            if item._parent_ref:
                parts = item._parent_ref.split(".")
                child_namespace = item
                while parts:
                    namespace_name = ".".join(parts)
                    parts = parts[:-1]
                    if namespace_name not in self._namespaces:
                        print("Creating implicit namespace",namespace_name,"with child namespace",child_namespace._namespace)
                        namespace = Namespace(namespace={"implicit":namespace_name}, data={"static":[child_namespace]})
                        self._waiting_merges[namespace_name] = self._waiting_merges.get(namespace_name, []) + [namespace]
                        child_namespace = namespace
                    else:
                        break #found something that exists
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
    #for namespace in n._namespaces:
    #print(n._namespaces['sr3'].keys())
    print(str(n._namespaces["sr3"].get(".gear.clothing_armor.general")))
    print(str(n._namespaces["sr3"].get("sr3.gear.clothing_armor.general.riot_shield_ballistic")))
    