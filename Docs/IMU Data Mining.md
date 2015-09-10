Inertial Measurement Units - Data Mining, Interpretation, and Visualisation
===========================================================================

# Raw Data


## Attitude and Heading Recognition System

## Transformation

## Noise Filter using Kalman Filter and Complimentary Filter

## Dimensionality Reduction using Principle Component Analysis

## Supervised Learning using Support Vector Machine

### Feature Vector Creation

[Definition] Feature Vector

Step 1: Sample Series
Since the inbound data is in time domain, discreet samples are not of greater significance here. Hence, to preserve the series properties, here we have sampled the inbound sensor reading in the order of arrival. A buffer having 16 samples in the correct order of arrival is used for further processing.
[Illustration] Arbitrary series.

Step 2: Sample Series overlapping
To preserve the arbitrary nature of inbound data, the obtained series is divided into multiple overlapping chunks. The buffer count, hence created, is increased by a factor of 16.

Step 3: Period Representation
Human motion is generally periodic - we observed a periodic pattern in the raw data visualization. To represent this, we arbirarily chose a template function defined as:
[Equation] fTemplate(x) = a Sin(bx + c) + d
Where,
    a is Amplitude,
    b is Phase,
    c is Phase Shift, and
    d is Vertical Shift

We used the Non-linear least square analysis of the data buffer to estimate the values of vIntermidiate = [a, b, c, d]. The solution of Non-linear least square analysis was obtained through Levenberg–Marquardt algorithm (LMA). We disregard the value of \d\, due to the fact that it only adds a vertical offset in the resulting wave, and does not contribute to either phase or the amplitude. Hence we obtain the Axes feature vector, vAxes = [a, b, c].

Step 4: Intermideate vector concatenation
The vectors are combined to form the feature matrix as follows:
mFeature = [vAxes(x), vAxes(y), vAxes(z)]

Step 5: Feature vector creation
To further obtain a feature that retains the properties exibited by mFeature, we find the eigenvector associated with mFeature. Since the eigenvalues may be of complex nature, we further reduced them by taking the absolute values complex number vector. Hence, we get the feature vector:
vFeature = [eig_amplitude, eig_phase, eig_phase_shift]

The feature vector \vFeature\ hence obtained was used to train the Support Vector Machine.

## Supervised Learning using Artificial Neural Networks

## Supervised Learning using


