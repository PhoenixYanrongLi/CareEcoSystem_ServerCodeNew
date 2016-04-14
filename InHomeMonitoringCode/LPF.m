%% Low pass filter design

clear all; close all; clc;

% filter design
N   = 5;   % number of filter taps
Fs  = 0.1; % sampling rate (Hz)
Fp  = 0.04;% passband cutoff (Hz)
Ap  = 0.1;% passband acceptable ripple (dB)
Ast = 60;  % stop band attenuation (dB)

% conversion to linear units
Rp  = (10^(Ap/20) - 1)/(10^(Ap/20) + 1);
Rst = 10^(-Ast/20);

% filter creation and testing
NUM1 = firceqrip(N,Fp/(Fs/2),[Rp Rst],'passedge');
NUM1 = NUM1/sum(NUM1)
NUM2 = [1 1 1 1 1];
fvtool(NUM1,1,NUM2,1,'Fs',Fs,'Color','White');
legend('designed','simple moving average');