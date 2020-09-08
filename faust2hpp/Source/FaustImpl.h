#ifndef __faust2hpp_FaustImpl_H__
#define __faust2hpp_FaustImpl_H__

#include <unordered_map>

#include "Meta.h"
#include "UI.h"

class FaustImpl
  : public UI
  , public Meta
{
public:
  FaustImpl() = default;
  ~FaustImpl() = default;

  FAUSTFLOAT* getParameter(const char* name)
  {
    const auto entry = parameterMap.find(name);
    return entry == parameterMap.end() ? nullptr : entry->second;
  }

  void setParameter(const char* name, FAUSTFLOAT* value)
  {
    const auto entry = parameterMap.find(name);
    if (entry != parameterMap.end())
      entry->second = value;
  }

  // blank implementations for UI
  virtual void declare(const char* key, const char* value){};
  virtual void openTabBox(const char* label){};
  virtual void openHorizontalBox(const char* label){};
  virtual void openVerticalBox(const char* label){};
  virtual void closeBox(){};
  virtual void addButton(const char* label, FAUSTFLOAT* zone){};
  virtual void addCheckButton(const char* label, FAUSTFLOAT* zone){};
  virtual void addVerticalSlider(
    const char* label,
    FAUSTFLOAT* zone,
    FAUSTFLOAT init,
    FAUSTFLOAT min,
    FAUSTFLOAT max,
    FAUSTFLOAT step){};
  virtual void addHorizontalSlider(
    const char* label,
    FAUSTFLOAT* zone,
    FAUSTFLOAT init,
    FAUSTFLOAT min,
    FAUSTFLOAT max,
    FAUSTFLOAT step){};
  virtual void
  // use UI entry to expose user parameters
  addNumEntry(const char* label, FAUSTFLOAT* zone, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT, FAUSTFLOAT)
  {
    if (zone == nullptr)
      return;
    parameterMap.insert_or_assign(label, zone);
  }
  virtual void addHorizontalBargraph(const char* label, FAUSTFLOAT* zone, FAUSTFLOAT min, FAUSTFLOAT max){};
  virtual void addVerticalBargraph(const char* label, FAUSTFLOAT* zone, FAUSTFLOAT min, FAUSTFLOAT max){};
  virtual void addSoundfile(const char* label, const char* filename, Soundfile** sf_zone){};

  // blank implememtation for Meta
  virtual void declare(const char* key, const char* value){};

private:
  std::unordered_map<const char*, FAUSTFLOAT*> parameterMap;
};

#endif
