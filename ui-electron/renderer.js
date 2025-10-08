import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import axios from 'axios';

// --- Global State ---
let selectedFilePath = null;
let convertedStepPath = null; // To store the path of the generated STEP file
let currentJobId = null;
let statusInterval = null;

// --- UI Elements ---
const openFileBtn = document.getElementById('open-file-btn');
const convertBtn = document.getElementById('convert-btn');
const renderBtn = document.getElementById('render-btn');
const renderProfileSelect = document.getElementById('render-profile-select');
const opticsBtn = document.getElementById('optics-btn'); // New button
const opticsProfileSelect = document.getElementById('optics-profile-select'); // New dropdown
const filePathDiv = document.getElementById('file-path');
const stepFileStatusDiv = document.getElementById('step-file-status');
const jobStatusDiv = document.getElementById('job-status');

// --- Event Listeners ---

// 1. Handle File Selection
openFileBtn.addEventListener('click', async () => {
  const filePath = await window.electronAPI.openFile();
  if (filePath) {
    selectedFilePath = filePath;
    filePathDiv.textContent = filePath;
    console.log('File selected:', filePath);
  }
});

// 2. Handle Job Request
convertBtn.addEventListener('click', async () => {
  if (!selectedFilePath) {
    alert('Please select a file first.');
    return;
  }

  console.log('Requesting STEP conversion for:', selectedFilePath);
  jobStatusDiv.textContent = 'Status: Requesting...';

  const jobInput = {
    files: [selectedFilePath],
    profiles: { "step": "fast_preview" },
    output_root: "/app/Output" // This could also be made configurable
  };

  try {
    const response = await axios.post('http://localhost:8000/jobs/convert', jobInput);
    currentJobId = response.data.job_id;
    jobStatusDiv.textContent = `Status: ${response.data.status}`;
    console.log('API Response Received:', response.data);

    // Start polling for status updates
    startStatusPolling(currentJobId);

  } catch (error) {
    console.error('API Request Failed:', error);
    jobStatusDiv.textContent = 'Status: API Request Failed';
    alert('Failed to create job. Check the console for details.');
  }
});

// 3. Handle Render Job Request
renderBtn.addEventListener('click', async () => {
  if (!convertedStepPath) {
    alert('Please run a successful STEP conversion first.');
    return;
  }

  const selectedProfile = renderProfileSelect.value;
  console.log(`Requesting render for ${convertedStepPath} with profile: ${selectedProfile}`);
  jobStatusDiv.textContent = 'Status: Requesting render...';

  const jobInput = {
    files: [convertedStepPath], // Use the path from the conversion result
    profiles: { "render": selectedProfile },
    output_root: "/tmp/solidworks_platform/Output" // Using a writable tmp directory
  };

  try {
    const response = await axios.post('http://localhost:8000/jobs/render', jobInput);
    currentJobId = response.data.job_id;
    jobStatusDiv.textContent = `Status: ${response.data.status}`;
    console.log('API Response Received:', response.data);

    // Start polling for status updates
    startStatusPolling(currentJobId);

  } catch (error) {
    console.error('Render API Request Failed:', error);
    jobStatusDiv.textContent = 'Status: Render Request Failed';
    alert('Failed to create render job. Check the console for details.');
  }
});

// 4. Handle Optics Job Request
opticsBtn.addEventListener('click', async () => {
  if (!convertedStepPath) {
    alert('Please run a successful STEP conversion first.');
    return;
  }

  const selectedProfile = opticsProfileSelect.value;
  console.log(`Requesting optics analysis for ${convertedStepPath} with profile: ${selectedProfile}`);
  jobStatusDiv.textContent = 'Status: Requesting optics analysis...';

  const jobInput = {
    files: [convertedStepPath], // Use the path from the conversion result
    profiles: { "optics": selectedProfile },
    output_root: "/tmp/solidworks_platform/Output"
  };

  try {
    const response = await axios.post('http://localhost:8000/jobs/optics', jobInput);
    currentJobId = response.data.job_id;
    jobStatusDiv.textContent = `Status: ${response.data.status}`;
    console.log('API Response Received:', response.data);

    startStatusPolling(currentJobId);

  } catch (error) {
    console.error('Optics API Request Failed:', error);
    jobStatusDiv.textContent = 'Status: Optics Request Failed';
    alert('Failed to create optics job. Check the console for details.');
  }
});


// --- Helper Functions ---

// 3. Poll for Job Status
function startStatusPolling(jobId) {
  // Clear any existing polling interval
  if (statusInterval) {
    clearInterval(statusInterval);
  }

  statusInterval = setInterval(async () => {
    try {
      const response = await axios.get(`http://localhost:8000/jobs/${jobId}`);
      const status = response.data.status;
      jobStatusDiv.textContent = `Status: ${status}`;
      console.log('Polling status:', status);

      // Stop polling if the job is complete
      if (status === 'success' || status === 'failure') {
        clearInterval(statusInterval);
        console.log('Polling stopped for job:', jobId);

        if (status === 'success') {
          // If a conversion job succeeded, store the output path for the next step
          if (response.data.task === 'convert') {
            // Assuming the output from the worker is the path to the STEP file
            const stepPath = response.data.details.output.split("created at ")[1]; // Simplistic parsing
            convertedStepPath = stepPath;
            stepFileStatusDiv.textContent = `STEP file ready: ${stepPath}`;
            jobStatusDiv.textContent = `Status: Conversion Succeeded. Ready for render.`;
          } else {
            jobStatusDiv.textContent = `Status: Success! Output: ${response.data.details.output_path}`;
          }
        } else {
          jobStatusDiv.textContent = `Status: Failure! Error: ${response.data.details.error}`;
        }
      }
    } catch (error) {
      console.error('Polling request failed:', error);
      jobStatusDiv.textContent = 'Status: Polling Failed';
      clearInterval(statusInterval);
    }
  }, 2000); // Poll every 2 seconds
}


// --- Three.js Scene Setup (as before) ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a1a);
scene.add(new THREE.AxesHelper(5));
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 5;
const canvas = document.getElementById('webgl-canvas');
const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);
const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(5, 5, 5);
scene.add(directionalLight);
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({ color: 0x00ff00, metalness: 0.3, roughness: 0.4 });
const cube = new THREE.Mesh(geometry, material);
scene.add(cube);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
const clock = new THREE.Clock();
function animate() {
  const elapsedTime = clock.getElapsedTime();
  cube.rotation.x = elapsedTime * 0.5;
  cube.rotation.y = elapsedTime * 0.5;
  controls.update();
  renderer.render(scene, camera);
  window.requestAnimationFrame(animate);
}
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
});
animate();
console.log('UI Initialized. Ready for user interaction.');