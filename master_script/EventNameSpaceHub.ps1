# First, ensure you're logged into Azure
Write-Output "Logging in to Azure..."
Connect-AzAccount

# Define variables for the resources
$resourceGroupName = "redpanda-rg"        # Resource Group name
$location = "EastUS"                      # Azure region
$namespaceName = "eagle-namespace"        # Event Hubs Namespace name
$eventHubName = "eaglehub"               # Event Hub name
$skuName = "Standard"                     # Pricing tier (Basic, Standard, or Premium)

try {
    # Check if resource group exists, create if it doesn't
    Write-Output "Checking resource group..."
    $resourceGroup = Get-AzResourceGroup -Name $resourceGroupName -ErrorAction SilentlyContinue
    if (-not $resourceGroup) {
        Write-Output "Creating resource group: $resourceGroupName"
        New-AzResourceGroup -Name $resourceGroupName -Location $location
    }

    # Create Event Hubs Namespace
    Write-Output "Creating Event Hubs Namespace: $namespaceName"
    $namespace = @{
        ResourceGroupName = $resourceGroupName
        Name = $namespaceName
        Location = $location
        SkuName = $skuName
    }
    New-AzEventHubNamespace @namespace

    # Wait for namespace to be ready
    Write-Output "Waiting for namespace to be ready..."
    Start-Sleep -Seconds 30

    # Create Event Hub within the namespace
    Write-Output "Creating Event Hub: $eventHubName"
    $eventHub = @{
        ResourceGroupName = $resourceGroupName
        Namespace = $namespaceName
        Name = $eventHubName
        RetentionInDays = 1              # Retention period in days (1-7 for Standard tier)
        PartitionCount = 2               # Number of partitions (2-32)
    }
    New-AzEventHub @eventHub

    Write-Output "Event Hub creation completed successfully!"
    Write-Output "Namespace: $namespaceName"
    Write-Output "Event Hub: $eventHubName"

} catch {
    Write-Error "An error occurred:"
    Write-Error $_.Exception.Message
}