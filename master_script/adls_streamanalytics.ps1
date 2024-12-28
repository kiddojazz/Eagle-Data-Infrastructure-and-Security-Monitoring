# Login to Azure
Write-Output "Logging in to Azure..."
Connect-AzAccount

# Variables
$resourceGroupName = "docker_rg"          # Use your existing resource group
$location = "EastUS"                      # Replace with your desired Azure region (if needed)
$storageAccountName = "eagleadls"  # Replace with your desired storage account name
$containerNames = @("checkpoints", "normal-transactions")
$streamAnalyticsJobName = "eagle-stream-analytics-job" # Replace with your desired job name

# Check if the Resource Group Exists
Write-Output "Verifying Resource Group: $resourceGroupName..."
if (-not (Get-AzResourceGroup -Name $resourceGroupName -ErrorAction SilentlyContinue)) {
    Write-Error "Resource Group $resourceGroupName does not exist. Please create it manually or specify a valid Resource Group."
    exit
} else {
    Write-Output "Resource Group $resourceGroupName exists. Proceeding with setup..."
}

# Create Storage Account (Data Lake Gen 2)
Write-Output "Creating Storage Account: $storageAccountName..."
$storageAccount = New-AzStorageAccount -ResourceGroupName $resourceGroupName `
                                        -Name $storageAccountName `
                                        -Location $location `
                                        -SkuName Standard_LRS `
                                        -Kind StorageV2 `
                                        -EnableHierarchicalNamespace $true
Write-Output "Storage Account $storageAccountName created successfully."

# Create Containers in the Storage Account
Write-Output "Creating containers in Storage Account: $storageAccountName..."
$storageContext = $storageAccount.Context
foreach ($containerName in $containerNames) {
    Write-Output "Creating container: $containerName..."
    New-AzStorageContainer -Name $containerName -Context $storageContext
    Write-Output "Container $containerName created successfully."
}

# Create Azure Stream Analytics Job
Write-Output "Creating Azure Stream Analytics Job: $streamAnalyticsJobName..."
New-AzStreamAnalyticsJob -ResourceGroupName $resourceGroupName `
                         -Name $streamAnalyticsJobName `
                         -Location $location `
                         -Sku Standard `
                         -OutputErrorPolicy Stop
Write-Output "Azure Stream Analytics Job $streamAnalyticsJobName created successfully."

Write-Output "Setup completed: Storage Account with containers and Stream Analytics Job."
