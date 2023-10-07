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

import common.util as ut
import common.minio_util as mutil
import json
from common.command_data import CommandData

class Minio():
    """
    Implementation of a Minio Command executor. It will require
    a user_data dictionary linked to a specific user.
    """

    def __init__(self, user_data):
        self._user_data = user_data        
        self._minio_access_key= ut.get_env_value(user_data,"MINIO_ACCESS_KEY")        
        self._minio_secret_key= ut.get_env_value(user_data,"MINIO_SECRET_KEY") 
        self._minio_host= ut.get_env_value(user_data,"MINIO_HOST") 
        self._minio_port= ut.get_env_value(user_data,"MINIO_PORT")
        self._minio_data_bucket= ut.get_env_value(user_data,"MINIO_DATA_BUCKET")
        self._minio_static_bucket= ut.get_env_value(user_data,"MINIO_STATIC_BUCKET")
        self.validate()

    def validate(self):
        """
        Validate that the provided user_data contains the appropriate
        metadata for being able to submit a postgres command.
        """
        if not self._minio_access_key or not self._minio_secret_key or not self._minio_host or not self._minio_port: 
            raise Exception("user does not have valid MINIO environment set")

    def _list_buckets(self, input:CommandData):
        print("**** listing user buckets")
        mo_client = mutil.build_mo_client(self._minio_host, self._minio_port,self._minio_access_key, self._minio_secret_key)
        buckets = mo_client.list_buckets()
        result = []

        for bucket in buckets:
            result.append({"bucket": bucket.name, "creation_date": str(bucket.creation_date)})

        input.result(result)
        input.status(200)

    def _list_bucket_content(self, bucket, input:CommandData):
        print(f"**** listing bucket {bucket} content")
        mo_client = mutil.build_mo_client(self._minio_host, self._minio_port,self._minio_access_key, self._minio_secret_key)
        objects = mo_client.list_objects(bucket_name=bucket, recursive= True)
        result = []
        
        for obj in objects:
            result.append({"name":obj.object_name,"last_modified": str(obj.last_modified), "size":obj.size})

        input.result(result)
        input.status(200)   

    def execute(self, input:CommandData):
        print(f"**** Minio command to execute {input.command()}")        
        try:
            if "ls" in input.command() and not "args" in input.get_metadata():                
                self._list_buckets(input)

            if "ls" in input.command() and "args" in input.get_metadata() and len(input.args()) > 0:
                self._list_bucket_content(input.args()[0], input)

        except Exception as e:
            input.result(f"could not execute minio command {e}")
            input.status(400)

        return input