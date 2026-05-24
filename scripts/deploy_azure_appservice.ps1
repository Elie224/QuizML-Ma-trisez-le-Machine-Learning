param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$Location,

    [Parameter(Mandatory = $true)]
    [string]$AcrName,

    [Parameter(Mandatory = $true)]
    [string]$AppServicePlan,

    [Parameter(Mandatory = $true)]
    [string]$WebAppName,

    [string]$ImageName = "qcm-api",
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/9] Verification connexion Azure..."
az account show 1>$null

Write-Host "[2/9] Creation du Resource Group..."
az group create --name $ResourceGroup --location $Location | Out-Null

Write-Host "[3/9] Creation de l'Azure Container Registry..."
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --admin-enabled true | Out-Null

Write-Host "[4/9] Build et push de l'image Docker dans ACR..."
az acr build --registry $AcrName --image "$ImageName`:$ImageTag" . | Out-Null

Write-Host "[5/9] Creation du plan App Service Linux..."
az appservice plan create --name $AppServicePlan --resource-group $ResourceGroup --sku B1 --is-linux | Out-Null

Write-Host "[6/9] Creation de la Web App containerisee..."
az webapp create --resource-group $ResourceGroup --plan $AppServicePlan --name $WebAppName --deployment-container-image-name "$AcrName.azurecr.io/$ImageName`:$ImageTag" | Out-Null

Write-Host "[7/9] Recuperation des identifiants ACR..."
$acrUser = az acr credential show --name $AcrName --query username -o tsv
$acrPass = az acr credential show --name $AcrName --query passwords[0].value -o tsv

if (-not $acrUser -or -not $acrPass) {
    throw "Impossible de recuperer les credentials ACR."
}

Write-Host "[8/9] Configuration de la Web App (image + registry + port)..."
az webapp config container set --name $WebAppName --resource-group $ResourceGroup --container-image-name "$AcrName.azurecr.io/$ImageName`:$ImageTag" --container-registry-url "https://$AcrName.azurecr.io" --container-registry-user $acrUser --container-registry-password $acrPass | Out-Null
az webapp config appsettings set --name $WebAppName --resource-group $ResourceGroup --settings WEBSITES_PORT=8000 | Out-Null

Write-Host "[9/9] Redemarrage de la Web App..."
az webapp restart --name $WebAppName --resource-group $ResourceGroup | Out-Null

$hostName = az webapp show --name $WebAppName --resource-group $ResourceGroup --query defaultHostName -o tsv

Write-Host ""
Write-Host "Deploiement termine."
Write-Host "URL: https://$hostName/"
