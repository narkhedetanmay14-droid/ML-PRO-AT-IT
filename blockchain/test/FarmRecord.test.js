const FarmRecord = artifacts.require("FarmRecord");

contract("FarmRecord", accounts => {
  const [owner] = accounts;
  it("deploys the contract", async () => {
    const instance = await FarmRecord.deployed();
    assert(instance.address);
  });

  it("adds and retrieves a farm record and emits an event", async () => {
    const instance = await FarmRecord.deployed();
    const hash = web3.utils.keccak256("demo-record");
    const tx = await instance.addRecord("REC-001", "F-1", "Test Farmer", "Rice", "Rice_Blast", "1 acre", "Demo", hash, {from: owner});
    assert(tx.logs.some(l => l.event === "FarmRecordAdded"));
    const r = await instance.getRecord("REC-001");
    assert.equal(r.recordId, "REC-001");
    assert.equal(r.farmerId, "F-1");
    assert.equal(r.crop, "Rice");
    assert.equal(r.recordHash, hash);
  });

  it("verifies the correct hash and rejects a wrong hash", async () => {
    const instance = await FarmRecord.deployed();
    const hash = web3.utils.keccak256("demo-record-2");
    await instance.addRecord("REC-002", "F-2", "Farmer Two", "Wheat", "Wheat_Rust", "2 acres", "Demo", hash, {from: owner});
    assert.equal(await instance.verifyRecord("REC-002", hash), true);
    assert.equal(await instance.verifyRecord("REC-002", web3.utils.keccak256("wrong")), false);
  });

  it("returns false for a nonexistent record", async () => {
    const instance = await FarmRecord.deployed();
    assert.equal(await instance.verifyRecord("NO-SUCH-RECORD", web3.utils.keccak256("x")), false);
    try { await instance.getRecord("NO-SUCH-RECORD"); assert.fail("Expected revert"); } catch (e) { assert(e.message.includes("Record not found")); }
  });
});
