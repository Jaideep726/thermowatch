function checkForCctvTrigger(feature) {
  const coords = feature.geometry.coordinates; // [lng, lat]
  const lng = coords[0];
  const lat = coords[1];
  
  // We check if the clicked point is the specific Jamnagar industrial fire (Lat: ~21.90, Lng: ~69.80)
  const isJamnagarRefinery = (
    feature.properties.classification === 'industrial' &&
    Math.abs(lat - 21.90) < 0.1 &&
    Math.abs(lng - 69.80) < 0.1
  );

  if (isJamnagarRefinery) {
    if (typeof showCctvQuerying === 'function') {
      showCctvQuerying();
    } else {
      console.log('Mock: showCctvQuerying() triggered');
    }
    
    setTimeout(() => {
      const videoPath = '../../../integration/cctv_mock_video.mp4';
      // Use a specific camera ID for this location
      const camId = 'RELIANCE-CAM-04';
      if (typeof showCctvConfirmed === 'function') {
        showCctvConfirmed(videoPath, camId);
      } else {
        console.log(`Mock: showCctvConfirmed('${videoPath}', '${camId}') triggered`);
      }
    }, 2000); // simulate ~2 second "checking" delay
  } else {
    // If they click any other point, reset the panel so the video disappears
    if (typeof resetCctvPanel === 'function') {
      resetCctvPanel();
    }
  }
}
