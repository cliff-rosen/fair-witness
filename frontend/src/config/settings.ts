// Environment-specific settings (mirrors the TableThat settings pattern).
const ENV = import.meta.env.MODE

const currentHost = window.location.hostname
const isLocalhost = currentHost === 'localhost' || currentHost === '127.0.0.1'

interface Settings {
  apiUrl: string
  appName: string
}

const developmentSettings: Settings = {
  apiUrl: isLocalhost ? 'http://localhost:8002' : `http://${currentHost}:8002`,
  appName: 'Fair Witness',
}

const productionSettings: Settings = {
  apiUrl: '/api-proxy', // configure for your deploy
  appName: 'Fair Witness',
}

const settings: Settings = ENV === 'production' ? productionSettings : developmentSettings

export default settings
