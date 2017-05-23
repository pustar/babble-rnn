import random
import numpy as np


class Generator:

  utils = None
  all_frames = None
  seed_seq_len = None
  frame_property_scaleup = None
  generate_len = None
  framelen = None
  
  def __init__(self, utils, all_frames, seed_seq_len, generate_len):
    self.utils = utils  
    self.all_frames = all_frames
    self.seed_seq_len = seed_seq_len
    self.generate_len = generate_len
  
  
  # process the sample prediction, ensuring it can be saved directly
  # into a Codec 2 "charbits" file
  def sample(self, preds, no_scale=False):
    preds = np.asarray(preds).astype('float32')
    if not no_scale:
      preds = np.multiply(preds,self.frame_property_scaleup)
    
    
    preds = np.round(preds)

    # it is necessary to cast to int before attempting to write to a file
    # to ensure that a real byte value is stored, not a byte 
    # representation of a floating point number
    intpreds = []
    for p in preds:
      intpreds.append(int(p))
    return np.array([intpreds], dtype=np.uint8) 


  
  def generate(self, iteration):
    utils = self.utils
    all_frames = self.all_frames
    seed_seq_len = self.seed_seq_len
    generate_len = self.generate_len
    framelen = self.framelen
    num_frames = len(all_frames)
    
    model_def = utils.model_def
    
    ofn = utils.open_output_file(iteration)
    utils.log("saving generated sample output to: ", ofn)
  
    utils.log("generating sample data of length: ", generate_len)
    start_index = 0 #random.randint(0, num_frames - seed_seq_len - 1)
    start_time = 1.0 * start_index / 40
    
    utils.log("seed sequence for generation starts at frame index: ", start_index, " (approx. ", int(start_time / 60), ":", int(start_time % 60), ")" )

    # pick the seed frame sequence starting at the random start index, with seed_seq_len frames
    seed_frame_seq = all_frames[start_index: start_index + seed_seq_len]
    
    # the output file should start with a copy of the seed frame sequence
    for frame in seed_frame_seq:
      utils.output_file.write(self.sample(frame))
      
    generated = []
    print('----- Generating with seed (just showing first): ', str(seed_frame_seq[0]) )
    
    for i in range(generate_len):
      # setup seed input
      x = np.zeros((1, seed_seq_len, framelen), dtype=np.float32)
      for t, frame in enumerate(seed_frame_seq):
        x[0, t] = frame

      # run the prediction for the next frame
      predicted_frame_props = model_def.model.predict(x, verbose=0)[0]
      # generate a Codec 2 frame from the predicted frame property values
      # we use the clumsy name predicted_frame_props to highlight that the frame properties are still
      # continuous (float) estimated values, rather than discrete Codec 2 values
      next_frame = predicted_frame_props
        
      # append the result to the generated set
      generated.append(next_frame)
      
      # update the seed frame sequence to remove the oldest frame and add the new predicted frame
      seed_frame_seq = seed_frame_seq[1:]
      seed_frame_seq.append(next_frame)

    # write the seed + generated data to the output file
    print("writing output file to disk")
    for frame in generated:
      utils.output_file.write(self.sample(frame))
        
    utils.output_file.close()
    utils.log("wrote frames: ", len(generated))
    
