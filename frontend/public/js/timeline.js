/**
 * Cyclone Evolution Timeline Player Engine
 * Implements Section 34 of SPEC.md.
 */

export class TimelinePlayer {
  constructor(options = {}) {
    this.steps = [];
    this.currentIndex = 0;
    this.isPlaying = false;
    this.timer = null;
    this.playbackIntervalMs = 550; // Smooth 550ms per step default

    this.onStepChange = options.onStepChange || (() => {});
    this.onPlayStateChange = options.onPlayStateChange || (() => {});
  }

  setTimelineData(steps) {
    this.steps = steps || [];
    this.currentIndex = 0;
    this.pause();
  }

  play() {
    if (this.isPlaying || this.steps.length === 0) return;
    if (this.currentIndex >= this.steps.length - 1) {
      // If at or past the end, start immediately from the beginning
      this.setStep(0);
    }
    this.isPlaying = true;
    this.onPlayStateChange(true);

    this.timer = setInterval(() => {
      if (this.currentIndex < this.steps.length - 1) {
        this.setStep(this.currentIndex + 1);
      } else {
        // Smoothly loop back to start
        this.setStep(0);
      }
    }, this.playbackIntervalMs);
  }

  pause() {
    this.isPlaying = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.onPlayStateChange(false);
  }

  togglePlay() {
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }
  }

  setStep(index) {
    if (index < 0 || index >= this.steps.length) return;
    this.currentIndex = index;
    try {
      this.onStepChange(this.steps[this.currentIndex], this.currentIndex, this.steps.length);
    } catch (err) {
      console.warn('Error in onStepChange callback:', err);
    }
  }

  stepForward() {
    this.pause();
    if (this.currentIndex < this.steps.length - 1) {
      this.setStep(this.currentIndex + 1);
    } else {
      this.setStep(0);
    }
  }

  stepBackward() {
    this.pause();
    if (this.currentIndex > 0) {
      this.setStep(this.currentIndex - 1);
    } else {
      this.setStep(this.steps.length - 1);
    }
  }

  setSpeed(multiplier = 1.0) {
    this.playbackIntervalMs = Math.max(200, Math.floor(800 / multiplier));
    if (this.isPlaying) {
      this.pause();
      this.play();
    }
  }
}
