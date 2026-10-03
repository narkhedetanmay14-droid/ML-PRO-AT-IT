// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract FarmRecord {
    struct Record {
        string recordId;
        string farmerId;
        string farmerName;
        string crop;
        string disease;
        string farmInfo;
        string recordInfo;
        bytes32 recordHash;
        uint256 timestamp;
        address creator;
    }

    mapping(string => Record) private records;
    mapping(string => bool) public recordExists;

    event FarmRecordAdded(string indexed recordId, bytes32 indexed recordHash, address indexed creator, uint256 timestamp);

    function addRecord(
        string memory recordId, string memory farmerId, string memory farmerName,
        string memory crop, string memory disease, string memory farmInfo,
        string memory recordInfo, bytes32 recordHash
    ) public {
        require(!recordExists[recordId], "Record already exists");
        records[recordId] = Record(recordId, farmerId, farmerName, crop, disease, farmInfo, recordInfo, recordHash, block.timestamp, msg.sender);
        recordExists[recordId] = true;
        emit FarmRecordAdded(recordId, recordHash, msg.sender, block.timestamp);
    }

    function getRecord(string memory recordId) public view returns (Record memory) {
        require(recordExists[recordId], "Record not found");
        return records[recordId];
    }

    function verifyRecord(string memory recordId, bytes32 expectedHash) public view returns (bool) {
        if (!recordExists[recordId]) return false;
        return records[recordId].recordHash == expectedHash;
    }
}
