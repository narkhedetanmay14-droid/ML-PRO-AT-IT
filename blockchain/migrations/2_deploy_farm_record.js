const FarmRecord = artifacts.require("FarmRecord");

module.exports = function (deployer) {
  deployer.deploy(FarmRecord);
};
