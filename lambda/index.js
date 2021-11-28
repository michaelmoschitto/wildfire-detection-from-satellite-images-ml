'use strict';

const axios = require('axios');

const url = "https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&LAYERS=MODIS_Aqua_CorrectedReflectance_TrueColor,MODIS_Aqua_Thermal_Anomalies_Day&CRS=EPSG:4326&TIME=2021-07-14&WRAP=DAY,DAY&BBOX=39.627921,-121.798852,40.627921,-120.798852&FORMAT=image/jpeg&WIDTH=455&HEIGHT=455&AUTOSCALE=FALSE&ts=1636752682648"


// const getImage =  async () => {
//     let imageData = {};
    
//     try {
//       imageData = await axios
//         .get(url, { responseType: 'arraybuffer' })
//         .then((response) => JSON.parse(Buffer.from(response.data, 'binary').toString()));
//       console.log('Image json successfully fetched');
//     } catch (error) {
//       console.error('Error fetching image json', error);
//       return reject(error);
//     }

//     const response = {
//       statusCode: 200,
//       isBase64Encoded: true,
//       body: imageBase64
//     };

//     return resolve(response);
// }

exports.handler = async (event, context) => {
    // TODO implement
    
    
    const img = await axios
    .get(url)
    // .then((response) => {
    //     console.log(response)
    //     return response
    // })
    // .then((response) => JSON.parse(response.data).toString());

    // console.log(img)
 
    var response = {
        statusCode: 200,
        body: img.toString("base64"),
        isBase64Encoded: true,
    };

    
    console.log(response)
    return response;
};



