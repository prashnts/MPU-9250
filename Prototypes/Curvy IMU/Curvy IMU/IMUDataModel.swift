//
//  IMUDataModel.swift
//  Curvy IMU
//
//  Created by Prashant Sinha on 26/09/15.
//  Copyright © 2015 Prashant Sinha. All rights reserved.
//

import Foundation


class IMUData {
    var _dat: [[String: Double]] {
        didSet {
            dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0)) {
                self.observer(self._dat.last!)
            }
        }
    }
    var sampling: Int
    let motion_kit: MotionKit
    var observer: ([String: Double]) -> ()
    
    init (obs: ([String: Double]) -> ()) {
        self.sampling = 100
        self._dat = [[String: Double]]()
        self.motion_kit = MotionKit()
        self.observer = obs
    }
    
    func log () {
        self.motion_kit.getDeviceMotionObject(0.01) {
            (deviceMotion) -> () in
            let dat: [String: Double] = [
                    "Accel_X": deviceMotion.gravity.x,
                    "Accel_Y": deviceMotion.gravity.y,
                    "Accel_Z": deviceMotion.gravity.z,
                    "RotRate_X": deviceMotion.rotationRate.x,
                    "RotRate_Y": deviceMotion.rotationRate.y,
                    "RotRate_Z": deviceMotion.rotationRate.z,
                    "MagX": deviceMotion.magneticField.field.x,
                    "MagY": deviceMotion.magneticField.field.y,
                    "MagZ": deviceMotion.magneticField.field.z,
                    "Yaw": deviceMotion.attitude.yaw,
                    "Pitch": deviceMotion.attitude.pitch,
                    "Roll": deviceMotion.attitude.roll
            ]
            self._dat.append(dat)
        }
    }
    
    func get_last() -> [String: Double]? {
        return self._dat.last
    }
}