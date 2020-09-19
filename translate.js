#! /usr/bin/env node

//const translate = require('google-translate-api');
//
//translate(process.argv[2], {from: 'ja', to: 'en'}).then(res => {
//    console.log(res.text);
//}).catch(err => {
//    console.error(err);
//});

const translate = require('google-translate-open-api').default;
//console.log(translate, translate.default);

translate(process.argv[2], {from: 'ja', to: 'en'}).then(res => {
	console.log(res.data);
}).catch(err => {
    console.error(err);
});