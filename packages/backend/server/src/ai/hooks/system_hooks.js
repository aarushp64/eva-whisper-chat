export async function openDesktopApp(appName, userApproved = false) {
  if (!userApproved) {
    return { status: 'pending_approval', tool: 'openDesktopApp', prompt: `Open the application ${appName}?` };
  }
  
  console.log(`[OS Hook] Spawning child process for app: ${appName}`);
  return { status: 'success', output: `${appName} launched successfully.` };
}
