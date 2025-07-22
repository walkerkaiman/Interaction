import os from 'os';
import si from 'systeminformation';

export async function getSystemStats() {
  // CPU usage: average over all cores
  const cpus = os.cpus();
  const cpuLoad = cpus.reduce((acc, cpu) => {
    const total = Object.values(cpu.times).reduce((a, b) => a + b, 0);
    return acc + (1 - cpu.times.idle / total);
  }, 0) / cpus.length;

  // Memory usage
  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const usedMem = totalMem - freeMem;
  const memUsage = usedMem / totalMem;

  // Temperature (systeminformation)
  let temperature = null;
  try {
    const tempInfo = await si.cpuTemperature();
    temperature = tempInfo.main || null;
  } catch (err) {
    temperature = null;
  }

  // Uptime
  const uptime = os.uptime();

  // Load averages
  const load = os.loadavg();

  return {
    cpu: cpuLoad, // 0..1
    memory: memUsage, // 0..1
    totalMem,
    usedMem,
    freeMem,
    temperature, // in Celsius, or null if unavailable
    uptime,
    load
  };
}

export async function getSystemInfo() {
  const [osInfo, system, cpu, mem, memLayout, graphics, disks, fs, net, battery, users] = await Promise.all([
    si.osInfo(),
    si.system(),
    si.cpu(),
    si.mem(),
    si.memLayout(),
    si.graphics(),
    si.diskLayout(),
    si.fsSize(),
    si.networkInterfaces(),
    si.battery(),
    si.users()
  ]);
  return {
    osInfo,
    system,
    cpu,
    mem,
    memLayout,
    graphics,
    disks,
    fs,
    net,
    battery,
    users
  };
}

export async function getProcesses() {
  return si.processes();
}

export async function getServices(serviceList?: string) {
  // serviceList: comma-separated string, e.g. 'mysql,nginx' or '*' for all
  return si.services(serviceList || '*');
} 