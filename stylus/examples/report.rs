use stylus_sdk::{
    prelude::*,
    alloy_primitives::U256,
};

#[solidity_storage]
pub struct Report {
    pub perpetrator_name: StorageString,
    pub encrypted_data: StorageString,
    pub overlap_count: StorageU32,
    pub created_at: StorageU64,
}

#[solidity_storage]
#[entrypoint]
pub struct ReportRegistry {
    reports: StorageMap<U256, Report>,
    total_reports: StorageU256,
    perpetrator_reports: StorageMap<StorageString, StorageVec<U256>>,
}

#[external]
impl ReportRegistry {
    pub fn constructor() -> Self {
        Self::default()
    }

    pub fn submit_report(&mut self, perpetrator_name: String, encrypted_data: String) -> Result<U256, Vec<u8>> {
        let report_id = self.total_reports.get();
        
        let mut report = Report::default();
        report.perpetrator_name.set(perpetrator_name.clone());
        report.encrypted_data.set(encrypted_data);
        report.overlap_count.set(0);
        report.created_at.set(stylus_sdk::block::timestamp());

        self.reports.insert(&report_id, &report);
        
        let mut perp_reports = self.perpetrator_reports
            .get(&StorageString::new(&perpetrator_name))
            .unwrap_or_default();
        perp_reports.push(report_id);
        self.perpetrator_reports.insert(&StorageString::new(&perpetrator_name), &perp_reports);
        
        self.total_reports.set(report_id + U256::from(1));
        
        Ok(report_id)
    }
    
    pub fn get_report(&self, report_id: U256) -> Result<(String, String, u32, u64), Vec<u8>> {
        let report = self.reports.get(&report_id)
            .ok_or_else(|| b"Report not found".to_vec())?;
        
        Ok((
            report.perpetrator_name.get(),
            report.encrypted_data.get(),
            report.overlap_count.get(),
            report.created_at.get()
        ))
    }
    
    pub fn get_perpetrator_reports(&self, perpetrator_name: String) -> Vec<U256> {
        self.perpetrator_reports
            .get(&StorageString::new(&perpetrator_name))
            .map(|reports| reports.iter().collect())
            .unwrap_or_default()
    }
    
    pub fn update_overlap_count(&mut self, report_id: U256, overlap_count: u32) -> Result<(), Vec<u8>> {
        let mut report = self.reports.get(&report_id)
            .ok_or_else(|| b"Report not found".to_vec())?;
        
        report.overlap_count.set(overlap_count);
        self.reports.insert(&report_id, &report);
        
        Ok(())
    }

    pub fn get_total_reports(&self) -> U256 {
        self.total_reports.get()
    }
}
