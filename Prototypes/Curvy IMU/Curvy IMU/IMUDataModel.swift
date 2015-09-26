//
//  IMUDataModel.swift
//  Curvy IMU
//
//  Created by Prashant Sinha on 26/09/15.
//  Copyright © 2015 Prashant Sinha. All rights reserved.
//

import Foundation


class IMUData {
    var _dat: [[String: Double]]
    var sampling: Int
    let motion_kit: MotionKit
    
    init (sampling: Int) {
        self.sampling = sampling
        self._dat = [[String: Double]]()
        self.motion_kit = MotionKit()
    }
    
    func log (data: [String: Double]) {
        self.motion_kit.getDeviceMotionObject(0.01) {
            (deviceMotion) -> () in
                self._dat.append([
                    "Accel_X": deviceMotion.gravity.x,
                    "Accel_Y": deviceMotion.gravity.y,
                    "Accel_Z": deviceMotion.gravity.z,
                    "RotRate_X": deviceMotion.rotationRate.x,
                    "RotRate_Y": deviceMotion.rotationRate.y,
                    "RotRate_Z": deviceMotion.rotationRate.z,
                    "MagX": deviceMotion.magneticField.x,
                    "MagY": deviceMotion.magneticField.y,
                    "MagZ": deviceMotion.magneticField.z,
                    "Yaw": deviceMotion.attitude.yaw,
                    "Pitch": deviceMotion.attitude.pitch,
                    "Roll": deviceMotion.attitude.roll
                ])
            
        }
    }
}