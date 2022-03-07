// Authors: Mohammed Alghazwi, Jeremie Decouchant, Fatih Turkmen
// Team: SmartCOmics
// Date: 18 Aug 2021

pragma solidity >=0.8.1;

// SPDX-License-Identifier: MIT

pragma experimental ABIEncoderV2;

contract PatientSharingPreferenceRepo {
    /*
     * The preferenceValues are ordered as follows:
     * [DEMOGRAPHICS, MENTAL_HEALTH, BIOSPECIMEN, FAMILY_HISTORY, GENETIC, GENERAL_CLINICAL_INFORMATION, SEXUAL_AND_REPRODUCTIVE_HEALTH]
    /*
     * Mappings
    */
    mapping(string => uint8) prefNameToIndex; // maps a preference name to its index in the ordered preferenceValues array
    
    mapping(uint256 => mapping (uint256 => patientData)) studyToPatientToTimePref; // mapping from studyId to patientId to recordTime and previous pref
    
    mapping(uint8 => mapping (uint256 => studyData)) prefToStudyData;
    /* 
     * structs
     */
    struct patientData {
        uint8 pref;
        uint256 recordTime;
    }
    
    struct studyData {
        uint256[] pidList;
        uint256[] timeList; 
        mapping (uint256 => uint256) pidToPos; // map pid -> pos
    }

    /*
     * set PreferenceName to index mapping
     */
    constructor() {
        prefNameToIndex["DEMOGRAPHICS"] = 0;
        prefNameToIndex["MENTAL_HEALTH"] = 1;
        prefNameToIndex["BIOSPECIMEN"] = 2;
        prefNameToIndex["FAMILY_HISTORY"] = 3;
        prefNameToIndex["GENETIC"] = 4;
        prefNameToIndex["GENERAL_CLINICAL_INFORMATION"] = 5;
        prefNameToIndex["SEXUAL_AND_REPRODUCTIVE_HEALTH"] = 6;
    }

    /*
     * Adds all preferences for one patient and one study at a time as an array of strings (preference names)
     * and an array of bool (preference values).
     *
     * Example:
     *
     * For patientId 2 and studyId 4 add preference ["RB1", "RET", "RYR1"] as [true, true, false].
     *
     * Also populates data structures used to keep track of pateintIds.
     */
    function addPreferences(
        uint _patientId,
        uint _studyId,
        uint256 _recordTime,
        string[] memory _preferenceNames,
        bool[] memory _preferenceValues
    ) public {
        
        // exit if more recent record exists
        if (studyToPatientToTimePref[_studyId][_patientId].recordTime > _recordTime)
            return; 

        // Create mask of preferences
        uint8 newPref = 0;
        for(uint256 i = 0; i < _preferenceNames.length; i++) {
            if (_preferenceValues[i]) {
                newPref |= uint8(1 << (6-prefNameToIndex[_preferenceNames[i]]));
            }
        }
            
        patientData storage pData = studyToPatientToTimePref[_studyId][_patientId];
        uint8 oldPref = pData.pref;
            
        // create/update recordtime for that patientId
        pData.recordTime = _recordTime;
        pData.pref = newPref;
 
        // Remove all previous insertions that needs to be removed
        for (uint8 curPref=oldPref; curPref!=0; curPref=(curPref-1)&oldPref){
            if (newPref & curPref != curPref) { // Patient to remove (all bits set in i are not set in newPref)
                
                studyData storage sd = prefToStudyData[curPref][_studyId];
                
                uint256 pos = prefToStudyData[curPref][_studyId].pidToPos[_patientId]-1;
                
                if (sd.pidList.length > 1) {
               
                    uint256 lastPid = sd.pidList[sd.pidList.length-1];
                    uint256 lastTime =  sd.timeList[sd.timeList.length-1];
                    
                    sd.pidList[pos] = lastPid;
                    sd.timeList[pos] = lastTime;
                    sd.pidToPos[lastPid] = pos+1; // move pid to cur pos
                }
                
                sd.pidToPos[_patientId] = 0;
                sd.pidList.pop();
                sd.timeList.pop();
            }
        }

        for (uint8 curPref=newPref; curPref!=0; curPref=(curPref-1)&newPref){
            studyData storage sd = prefToStudyData[curPref][_studyId];
            if (sd.pidToPos[_patientId] == 0) {
                sd.pidList.push(_patientId);
                sd.timeList.push(_recordTime);
                sd.pidToPos[_patientId] = sd.pidList.length;
            } else { // Update record time 
                uint256 pos = sd.pidToPos[_patientId]-1;
                sd.timeList[pos] = _recordTime;
            }
        }
    }

    /*
     * Takes a studyId and an array of preference names and returns all patientIds that have conscented to all preference names in the list.
     */
    function getConsentingPatientIds(
        uint _studyId,
        string[] memory _requestedSitePreferences
    ) public view returns (uint[] memory) {

        // Create mask of preferences
        uint8 preferenceBits = 0;
        for(uint256 i = 0; i < _requestedSitePreferences.length; i++) {
            preferenceBits |= uint8(1 << (6-prefNameToIndex[_requestedSitePreferences[i]]));
        }

        return prefToStudyData[preferenceBits][_studyId].pidList;
    }
    
}
