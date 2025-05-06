const sass = require('sass');

const result = sass.compile('index.scss');
console.log(result.css);