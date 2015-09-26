//
//  FirstViewController.swift
//  Curvy IMU
//
//  Created by Prashant Sinha on 25/09/15.
//  Copyright © 2015 Prashant Sinha. All rights reserved.
//

import UIKit

class FirstViewController: UIViewController {

    @IBOutlet weak var axx: UILabel!

    func update_label(dat: [String: Double]) {
        axx.text = String(dat["Accel_X"])
    }
    
    override func viewDidLoad() {
        super.viewDidLoad()
        // Do any additional setup after loading the view, typically from a nib.
        let probe: IMUData = IMUData(obs: self.update_label)

        probe.log()
        
    }

    override func didReceiveMemoryWarning() {
        super.didReceiveMemoryWarning()
        // Dispose of any resources that can be recreated.
    }


}

