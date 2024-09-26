import pandas as pd
from azure.mgmt.compute import ComputeManagementClient
from azure.identity import ClientSecretCredential

Subscription_Id = "xxx" #Your subscription ID
Tenant_Id = "xxx" #Your AD tenant ID
Client_Id = "xxx" #Your service principal client ID
Secret = "xxx" #Your service principal secret

credential = ClientSecretCredential(
        client_id=Client_Id,
        client_secret=Secret,
        tenant_id=Tenant_Id
        )

compute_client = ComputeManagementClient(credential, Subscription_Id)

skus = compute_client.resource_skus.list() #get the SKUs available
list_skus = []
for i in skus:
    list_skus.append(i.as_dict())

list_skus_final = [i for i in list_skus if i['resource_type']=="virtualMachines"]

for n in list_skus_final:
    n['cores'] = n['capabilities'][2]['value']

vm_skus = pd.DataFrame(list_skus_final)
vm_skus.rename(columns={"name":"vm_size"}, inplace=True)

vm_list = compute_client.virtual_machines.list_all() #get all VMs created in the subscription
vms = []
for vm in vm_list:
    d = vm.as_dict()
    if "tags" in d.keys():
        if "Vendor" in d['tags']:
            if d['tags']['Vendor'] == "Databricks":
                vms.append(d)

for vm in vms:
    if 'DatabricksInstancePoolId' not in vm['tags'] and 'SqlEndpointId' not in vm['tags'] :
        vm['vm_size'] = vm['hardware_profile']['vm_size']
        if 'ClusterName' in vm['tags']:
          vm['cluster_name'] = vm['tags']['ClusterName']
          vm['cluster_id'] = vm['tags']['ClusterId']
    elif 'SqlEndpointId' in vm['tags']:
      vm['vm_size'] = vm['hardware_profile']['vm_size']
      vm['sql_datawarehouse_id'] = vm['tags']['SqlEndpointId']
      vm['cluster_name'] = ""
      vm['cluster_id'] = vm['tags']['ClusterId']
    elif 'DatabricksInstancePoolId' in vm['tags']:
      vm['vm_size'] = vm['hardware_profile']['vm_size']
      vm['pool_id'] = vm['tags']['DatabricksInstancePoolId']
      if 'ClusterName' in vm['tags']:
        vm['cluster_name'] = vm['tags']['ClusterName']
        vm['cluster_id'] = vm['tags']['ClusterId']
    array = vm['id'].split("/")
    vm['resource_group'] = array[4].lower()
    if "databricks-rg" in vm['resource_group']:
        vm['workspace_name'] = vm['resource_group'][14:-14].lower()
    vm['workspace_id'] = vm['tags']['DatabricksEnvironment'][10]     

vms_df = pd.DataFrame(vms)
vms_final = vms_df.merge(vm_skus[["vm_size","cores","family"]].drop_duplicates(),how="left",on="vm_size")
vms_final.drop(["hardware_profile","network_profile","os_profile","storage_profile","resource_group","tags","type","vm_id"] ,axis=1, inplace=True)
vms_final = vms_final.rename(columns={"name":"vm_name"})[["workspace_name","workspace_id","pool_id","sql_datawarehouse_id","cluster_id","cluster_name","location","family","vm_name","vm_size","cores"]]
vms_final[['cores']] = vms_final[["cores"]].astype('int64')

#number of cores used from each SKU family for specific location for specific cluster within a certain workspace

print('VMs that belong to clusters:')
print(vms_final.loc[(pd.isnull(vms_final['pool_id']) & pd.isnull(vms_final['sql_datawarehouse_id']))]\
                     .groupby(["workspace_name","cluster_name","location","family"]).sum())
print("")
if 'pool_id' in vms_final.columns:
    print('VMs that belong to a pool:')
    print(vms_final.groupby(["workspace_name","pool_id","location","family"]).sum())
    print("")
if 'sql_datawarehouse_id' in vms_final.columns: 
    print('VMs that belong to SQL warehouses:')
    print(vms_final.groupby(["workspace_name","sql_datawarehouse_id","location","family"]).sum())


#Total number of cores used for each family in certain location for each Databricks workspace:
vms_final.groupby(["workspace_name","location","family"]).sum() 

#Total number of cores used by Azure Databricks in the subscription per SKU family per region:
vms_final.groupby(["location","family"]).sum() 
