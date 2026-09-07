function checkForCctvTrigger(features) {
  const highConfidenceWildfire = features.find(
    f => f.properties.classification === 'wildfire' && f.properties.frp > 80
  );
  if (highConfidenceWildfire) {
    if (typeof showCctvQuerying === 'function') {
      showCctvQuerying();
    } else {
      console.log('Mock: showCctvQuerying() triggered');
    }
    
    setTimeout(() => {
      const videoPath = '../../../integration/cctv_mock_video.mp4';
      const camId = 'JMG-CAM-2847';
      if (typeof showCctvConfirmed === 'function') {
        showCctvConfirmed(videoPath, camId);
      } else {
        console.log(`Mock: showCctvConfirmed('${videoPath}', '${camId}') triggered`);
      }
    }, 2000); // simulate ~2 second "checking" delay
  }
}
