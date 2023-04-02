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
import nuvolaris.config as cfg
import nuvolaris.testutil as tu
import nuvolaris.kube as kube
import nuvolaris.workflows as wfx

cfg.clean()
assert(cfg.configure(tu.load_sample_config()))

name = "workflow-test"
spec = tu.load_sample_config(name)
job = wfx.generate_job(name, spec, "create")
print(job)
kube.apply(job)

!kubectl -n nuvolaris wait --for=condition=complete job/workflow-test  --timeout=600s

l = !kubectl -n nuvolaris logs job/workflow-test -c first

check = {"_STEP_=start", "_WORKFLOW_=nginx","_ACTION_=create", "_APIHOST_=undefined-apihost", "VAL1=alpha", "VAL2=beta"}

assert(len(set(l) & check) == len(check))

l = !kubectl -n nuvolaris logs job/workflow-test -c second

