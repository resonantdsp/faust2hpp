#ifndef __FAUSTPROCESSOR__
#define __FAUSTPROCESSOR__

class FaustProcessor
{
public:
  FaustProcessor() = default;
  virtual ~FaustProcessor() = default;
  virtual void reset() = 0;
  virtual void prepare(int sampleRate) = 0;
  virtual void process(int count, FAUSTFLOAT** buffer) = 0;
};

#endif