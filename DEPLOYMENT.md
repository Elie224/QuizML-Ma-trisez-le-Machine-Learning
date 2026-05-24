# Deploiement QCM ML

## 1) Demarrage local (Windows PowerShell)

Installer les dependances:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r .\requirements-deploy.txt
```

Lancer l'API QCM:

```powershell
& .\.venv\Scripts\python.exe -m uvicorn qcm_api_fr:app --host 0.0.0.0 --port 8000
```

Verifier la sante:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/health
```

## 2) Appels API QCM

Creer une session:

```powershell
$body = @{ count = 5; topic = "evaluation" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/qcm/sessions -ContentType "application/json" -Body $body
```

Repondre a une question:

```powershell
$answer = @{ choice_index = 1 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/qcm/sessions/<SESSION_ID>/answer -ContentType "application/json" -Body $answer
```

Lister les themes:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/qcm/topics
```

## 3) Deploiement Docker

Build:

```powershell
docker build -t qcm-ml-api:latest .
```

Run:

```powershell
docker run --rm -p 8000:8000 qcm-ml-api:latest
```

## 4) Deploiement Azure App Service (Container)

Prerequis:

- Azure CLI installee et connectee (`az login`)
- Subscription Azure active

Variables recommandees (PowerShell):

```powershell
$RG = "rg-qcm-ml"
$LOC = "francecentral"
$ACR = "qcmmlacr001"
$PLAN = "plan-qcm-ml"
$APP = "qcm-ml-api-001"
$IMAGE = "qcm-api"
$TAG = "v1"
```

Option rapide (script automatique):

```powershell
./scripts/deploy_azure_appservice.ps1 -ResourceGroup $RG -Location $LOC -AcrName $ACR -AppServicePlan $PLAN -WebAppName $APP -ImageName $IMAGE -ImageTag $TAG
```

Option manuelle (commandes Azure CLI):

```powershell
az group create --name $RG --location $LOC

az acr create --resource-group $RG --name $ACR --sku Basic --admin-enabled true

az acr build --registry $ACR --image "$IMAGE:$TAG" .

az appservice plan create --name $PLAN --resource-group $RG --sku B1 --is-linux

az webapp create --resource-group $RG --plan $PLAN --name $APP --deployment-container-image-name "$ACR.azurecr.io/$IMAGE:$TAG"

$ACR_USER = az acr credential show --name $ACR --query username -o tsv
$ACR_PASS = az acr credential show --name $ACR --query passwords[0].value -o tsv

az webapp config container set --name $APP --resource-group $RG --container-image-name "$ACR.azurecr.io/$IMAGE:$TAG" --container-registry-url "https://$ACR.azurecr.io" --container-registry-user $ACR_USER --container-registry-password $ACR_PASS

az webapp config appsettings set --name $APP --resource-group $RG --settings WEBSITES_PORT=8000

az webapp restart --name $APP --resource-group $RG
```

Verifier le deploiement:

```powershell
az webapp show --name $APP --resource-group $RG --query defaultHostName -o tsv
```

Puis ouvrir:

```powershell
https://<defaultHostName>/
```
