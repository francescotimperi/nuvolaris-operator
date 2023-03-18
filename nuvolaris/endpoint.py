# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import kopf, logging, json, time
import nuvolaris.kube as kube
import nuvolaris.kustomize as kus
import nuvolaris.config as cfg
import nuvolaris.openwhisk as openwhisk
import nuvolaris.util as util
import urllib.parse

def get_ingress(namespace="ingress-nginx"):
    ingress = kube.kubectl("get", "service/ingress-nginx-controller", namespace=namespace,jsonpath="{.status.loadBalancer.ingress[0]}")
    if ingress:
        return ingress
    
    return None

def create(owner=None):
    runtime = cfg.get('nuvolaris.kube')
    tls = cfg.get('components.tls')
    
    apihost = ""

    if runtime in ["k3s","microk8s"]:
        apihost = openwhisk.apihost(None)
    else:
        namespace = util.get_ingress_namespace(runtime)
        apihost = openwhisk.apihost(get_ingress(namespace))    

    logging.info(f"*** Configuring ingress for apihost={apihost}")
    
    openwhisk.annotate(f"apihost={apihost}")
    url = urllib.parse.urlparse(apihost)

    hostname = url.hostname    
    ingress_class = cfg.detect_ingress_class()

    data = {
        "hostname":hostname,
        "ingress_class":ingress_class
    }

    tpl = (runtime == "kind" or not tls) and "apihost-in-http.yaml" or "apihost-in-https.yaml";
    logging.info(f"*** Configuring host {hostname} endpoint for openwhisk controller using {tpl}")

    kust = kus.patchTemplates("openwhisk-endpoint", [tpl], data)
    spec = kus.restricted_kustom_list("openwhisk-endpoint", kust, templates=[],templates_filter=[tpl],data=data)

    if owner:
        kopf.append_owner_reference(spec['items'], owner)
    else:
        cfg.put("state.endpoint.spec", spec)
        
    return kube.apply(spec)

def delete():
    spec = cfg.get("state.endpoint.spec")
    res = False
    if spec:
        res = kube.delete(spec)
        return res
