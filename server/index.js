const corelink = require('corelink-client')

const config = {
  ControlPort: 20012,
  ControlIP: '127.0.0.1',
  // ControlIP: process.env.CORELINK_HOST,
  autoReconnect: false,
  /*
    for service in a local network please replace the certificate with the appropriate version
  cert: '<corelink-tools-repo>/config/ca-crt.pem'
  */
  cert: process.env.CERT_PATH
}

const username = process.env.CORELINK_USERNAME
const password = process.env.CORELINK_PASSWORD

const workspace = 'Holodeck'
const protocol = 'tcp'
const datatype = 'distance'

const run = async () => {
  if (await corelink.connect({ username, password }, config).catch((err) => { console.log(err) })) {
    await corelink.createReceiver({
      workspace,
      protocol,
      type: datatype,
      echo: true,
      alert: true,
    }).catch((err) => { console.log(err) })

    corelink.on('receiver', async (data) => {
      const options = { streamIDs: [data.streamID] }
      await corelink.subscribe(options)
    })

    corelink.on('data', (streamID, data, header) => {
      console.log(streamID, data.toString(), JSON.stringify(header))
    })
  }
}

run()
