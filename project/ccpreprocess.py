import os, time
import numpy as np

dir_path = os.path.abspath('')

def sine_wave(f, sr, duration, phase=0):
    return np.array([np.sin(2*np.pi*f*(t/sr)+phase) for t in range(int(sr*duration))])

def softmax(matrix):
    x = matrix - np.max(matrix, axis=1).reshape(-1,1)
    exp_x = np.exp(x)
    sum_x = np.sum(exp_x, axis=1).reshape(-1,1)
    return exp_x / sum_x

class Music():
    def __init__(self, title, y, sr, tempo, sections, beats_per_section, slices_per_beat,
                f_min=-24, f_max=12, A4=440):
        '''
            Args:
                y : wave array
                sr : sampling rate
                tempo : beats per minute (bpm)
                sections : number of sections to simplify
                beats_per_section : number of beats per section
                slices_per_beat : number of slices per beat
                f_min : minimum frequency to analyze
                f_max : maximum frequency to analyze
                A4 : default Hz of A4
        '''
        self.length_per_slice = int(60 / tempo * sr / slices_per_beat) # the length of the array per slice
        self.title = title
        self.y = y[:self.length_per_slice * slices_per_beat * beats_per_section * sections]
        self.sr = sr
        self.tempo = tempo
        self.sections = sections
        self.beats_per_section = beats_per_section
        self.slices_per_beat = slices_per_beat
        self.ks = [A4 * 2**(f/12) for f in range(f_min, f_max+1)] # frequencies to analyze

    def fourier(self, frame, k):
        frame_copy = np.array(frame.copy(), dtype='complex_')
        for w in range(len(frame_copy)):
            dt = 1 / self.sr
            frame_copy[w] = np.exp(-1j*2*np.pi*k*w*dt) * complex(frame_copy[w])
        return abs(sum(frame_copy))

    def extract_amplitude_matrix(self, normalized=True):
        amplitude_matrix = []
        print("extracting ... ", end='')
        process_counter = 0
        total_frames = self.slices_per_beat * self.beats_per_section * self.sections
        for frame in range(total_frames):
            if frame/total_frames > process_counter:
                process_counter += 0.1
                print('#', end='')
            start_index = frame * self.length_per_slice
            end_index   = (frame+1) * self.length_per_slice
            amplitude   = np.array([self.fourier(self.y[start_index:end_index], k) for k in self.ks])
            amplitude_matrix.append(amplitude)
        print(" extraction complete ...", end='')
        amplitude_matrix = np.array(amplitude_matrix)
        if normalized:
            amplitude_matrix = amplitude_matrix / np.max(amplitude_matrix)

        return np.array(amplitude_matrix)

    def composite_wave(self, amplitude_matrix, use_softmax=False):
        composition = np.array([])
        duration = 60/self.tempo/self.slices_per_beat
        if use_softmax:
            amplitude_matrix =softmax(amplitude_matrix)
        else:
            amplitude_matrix = amplitude_matrix
        for frame in range(amplitude_matrix.shape[0]):
            superposition = amplitude_matrix[frame][0] * sine_wave(f=self.ks[0], sr=self.sr, duration=duration)
            for i in range(1, amplitude_matrix.shape[1]):
                superposition += amplitude_matrix[frame][i] * sine_wave(f=self.ks[i], sr=self.sr, duration=duration)
            composition = np.hstack((composition, superposition))
        return composition