"""
This script loops over all participants and all sessions and prepares the data for classification analysis.

- [ ] Only include the triggers from README when saving data

"""

import sys
from pathlib import Path
import json
import mne
import numpy as np

# local imports
sys.path.append(str(Path(__file__).parents[1]))
from utils import preprocess_data_sensorspace, epochs_to_sourcespace, morph_stcs_label




def main():
    path = Path(__file__).parents[1]

    fs_subjects_dir = Path("/work/835482") # path to freesurfer subjects directory
    MEG_data_path = Path("/work/834761")
    subjects = ["0108", "0109", "0110", "0111", "0112", "0113", "0114", "0115"]
    recording_names = ['001.self_block1',  '002.other_block1', '003.self_block2', '004.other_block2', '005.self_block3',  '006.other_block3']
    outpath = path / "data"
    fwd_fsaverage_path = fs_subjects_dir / "fsaverage" / "bem" / "fsaverage-oct-6-src.fif"

    ICA_path = path / "ICA"


    label = 'parsopercularis-lh'
    # load session information with reject criterion
    with open(path / 'session_info.txt', 'r') as f:
        file = f.read()
        session_info = json.loads(file)
    
    # load src for fsaverage
    src_fsaverage = mne.read_source_spaces(fwd_fsaverage_path)


    for subject in subjects:
        subject_info = session_info[subject]
        subject_path = MEG_data_path / subject
        
        # find the folder with MEG data and not the folder with MRI data
        subject_meg_path = list(subject_path.glob("*_000000"))[0]

        # make a folder for the subject
        subject_outpath = outpath / subject

        if not subject_outpath.exists():
            subject_outpath.mkdir(parents=True)

        for idx, recording_name in enumerate(recording_names):
            subject_session_info = subject_info[recording_name]

            fif_file_path = list((subject_meg_path / "MEG" / recording_name / "files").glob("*.fif"))[0]

            ICA_path_sub = ICA_path / subject / f"{recording_name}-ica.fif"

            epochs = preprocess_data_sensorspace(fif_file_path, subject_session_info["bad_channels"], subject_info["reject"], ICA_path_sub, subject_session_info["noise_components"])

            # load forward solution
            fwd_fname = recording_name[4:] + '-oct-6-src-' + '5120-fwd.fif'
            fwd = mne.read_forward_solution(fs_subjects_dir / subject / 'bem' / fwd_fname)

            # get source time courses
            stcs = epochs_to_sourcespace(epochs, fwd)

            # morph from subject to fsaverage
            morph_subject_path = fs_subjects_dir / subject / "bem" / f"{subject}-oct-6-src-morph.h5"
            X_tmp = morph_stcs_label(morph_subject_path, stcs, fs_subjects_dir, label)
            y_tmp = epochs.events[:, -1]

            if idx == 0:
                X = X_tmp
                y = y_tmp
            else:
                X = np.concatenate((X, X_tmp))
                y = np.concatenate((y, y_tmp))

        print(X.shape)
        print(y.shape)
        
        # save the data
        np.save(subject_outpath / f"X_{label}.npy", X)
        np.save(subject_outpath / f"y_{label}.npy", y)
        


if __name__ in "__main__":
    main()    