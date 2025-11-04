const path = require('path');

module.exports = {
  mode: 'development',
  entry: {
    bundle: './src/index.js',
    step1: './src/steps/step1.js',
    step2: './src/steps/step2.js',
    step3: './src/steps/step3.js',
    step4: './src/steps/step4.js',
    step5: './src/steps/step5.js',
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist'),
  },
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist'),
    },
    compress: true,
    port: 8080,
    open: true,
  },
};
