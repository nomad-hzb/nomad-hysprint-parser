#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from nomad.datamodel import EntryArchive
from nomad.parsing import MatchingParser

from hysprint_s import (HySprint_JVmeasurement,
                        HySprint_TimeResolvedPhotoluminescence,
                        HySprint_EQEmeasurement,
                        HySprint_PLmeasurement,
                        HySprint_Measurement,
                        HySprint_UVvismeasurement,
                        HySprint_trSPVmeasurement,
                        HZB_EnvironmentMeasurement,
                        HZB_NKData)

from baseclasses.solar_energy import SolarCellEQECustom


from baseclasses.helper.archive_builder.jv_archive import get_jv_archive
from baseclasses.helper.file_parser.jv_parser import get_jv_data

from baseclasses.helper.utilities import set_sample_reference, create_archive, get_entry_id_from_file_name, get_reference
from nomad.datamodel.data import (
    EntryData,
)
from nomad.metainfo import (
    Quantity,
)
from nomad.datamodel.metainfo.basesections import (
    Entity,
)
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
)

import json
import os
import datetime

'''
This is a hello world style example for an example parser/converter.
'''

class RawFileHZB(EntryData):
    processed_archive = Quantity(
        type=Entity,
        a_eln=ELNAnnotation(
            component='ReferenceEditQuantity',
        )
    )

class HySprintParser(MatchingParser):
    def __init__(self):
        super().__init__(
            name='parsers/hysprint', code_name='HYSPRINT', code_homepage='https://www.example.eu/',
            supported_compressions=['gz', 'bz2', 'xz']
        )

    def parse(self, mainfile: str, archive: EntryArchive, logger):
        # Log a hello world, just to get us started. TODO remove from an actual parser.

        mainfile_split = os.path.basename(mainfile).split('.')
        notes = ''
        if len(mainfile_split) > 2:
            notes = mainfile_split[1]
        entry = HySprint_Measurement()
        if mainfile_split[-1] == "txt" and mainfile_split[-2] == "jv":
            entry = HySprint_JVmeasurement()
        if mainfile_split[-1] == "txt" and mainfile_split[-2] == "spv":
            entry = HySprint_trSPVmeasurement()
        if mainfile_split[-1] == "txt" and mainfile_split[-2] == "eqe":
            header_lines = 9
            sc_eqe = SolarCellEQECustom()
            sc_eqe.eqe_data_file = os.path.basename(mainfile)
            sc_eqe.header_lines = header_lines
            entry = HySprint_EQEmeasurement()
            entry.data = sc_eqe
        if mainfile_split[-2] == "pl":
            entry = HySprint_PLmeasurement()
        if mainfile_split[-2] == "uvvis":
            entry = HySprint_UVvismeasurement()
            entry.data_file = [os.path.basename(mainfile)]
        if mainfile_split[-1] in ["txt"] and mainfile_split[-2] == "env":
            entry = HZB_EnvironmentMeasurement()
        if  mainfile_split[-1] in ["nk"]:
            entry = HZB_NKData()
        archive.metadata.entry_name = os.path.basename(mainfile)

        if not mainfile_split[-1] in ["nk"]:
            search_id = mainfile_split[0]
            set_sample_reference(archive, entry, search_id)

            entry.name = f"{search_id} {notes}"
            entry.description = f"Notes from file name: {notes}"

        if not mainfile_split[-2] == "eqe" and not mainfile_split[-2] == "uvvis":
            entry.data_file = os.path.basename(mainfile)
        entry.datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        file_name = f'{os.path.basename(mainfile)}.archive.json'
        eid = get_entry_id_from_file_name(file_name, archive)
        archive.data = RawFileHZB(processed_archive=get_reference(archive.metadata.upload_id, eid))
        create_archive(entry, archive, file_name)
