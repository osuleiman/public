Install-WindowsFeature -Name DNS -IncludeManagementTools
Set-DnsServerForwarder -UseRootHint $false
