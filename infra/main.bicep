param location string = resourceGroup().location
param environmentName string = 'exzing-env'

resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: '${environmentName}-plan'
  location: location
  tags: { 'azd-env-name': environmentName }
  sku: { name: 'B1' }
  kind: 'linux'
  properties: { reserved: true }
}

resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: 'exzing-reservoir-agent'
  location: location
  tags: { 'azd-service-name': 'web' }
  kind: 'app,linux,python'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      appCommandLine: 'python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true'
      alwaysOn: true
    }
  }
}

resource appSettings 'Microsoft.Web/sites/config@2022-03-01' = {
  parent: webApp
  name: 'appsettings'
  properties: {
    'WEBSITES_PORT': '8000'
    'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true'
  }
}
