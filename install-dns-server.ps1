Install-WindowsFeature -Name DNS -IncludeManagementTools
Set-DnsServerForwarder -UseRootHint $false
Set-DnsServerRecursion -Enable 0
