
'use strict';

const axios = require('axios');

if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config();
}

const url = "https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&LAYERS=MODIS_Aqua_CorrectedReflectance_TrueColor,MODIS_Aqua_Thermal_Anomalies_Day&CRS=EPSG:4326&TIME=2021-07-14&WRAP=DAY,DAY&BBOX=39.627921,-121.798852,40.627921,-120.798852&FORMAT=image/jpeg&WIDTH=455&HEIGHT=455&AUTOSCALE=FALSE&ts=1636752682648"

const run = () => {
  return new Promise(async (resolve, reject) => {
    console.log('Lambda called');

    let imageData = {};

    try {
      imageData = await axios
        .get(url, { responseType: 'arraybuffer' })
        .then((response) => JSON.parse(Buffer.from(response.data, 'binary').toString()));
      console.log('Image json successfully fetched');
    } catch (error) {
      console.error('Error fetching image json', error);
      return reject(error);
    }

    if (!imageData.urls || !imageData.urls.small) {
      const error = 'Small image url is missing in unsplash json';
      console.error(error);
      return reject(new Error(error));
    }

    let imageBase64 = '';
    console.log(`Fetch a small image from ${imageData.urls.small}`);

    try {
      imageBase64 = await axios
        .get(imageData.urls.small, { responseType: 'arraybuffer' })
        .then((response) => Buffer.from(response.data, 'binary').toString('base64'));
      console.log('A small image successfully fetched');
    } catch (error) {
      console.error('Error fetching a small image', error);
      return reject(error);
    }

    const response = {
      statusCode: 200,
      isBase64Encoded: true,
      body: imageBase64
    };
    console.log(`Response: ${JSON.stringify(response, null, 2)}`);

    return resolve(response);
  });
};

module.exports.handler = run;
