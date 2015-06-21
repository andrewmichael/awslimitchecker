"""
awslimitchecker/tests/services/test_autoscaling.py

The latest version of this package is available at:
<https://github.com/jantman/awslimitchecker>

################################################################################
Copyright 2015 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of awslimitchecker, also known as awslimitchecker.

    awslimitchecker is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    awslimitchecker is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with awslimitchecker.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/pydnstest> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

from mock import Mock, patch, call
from boto.ec2.autoscale import AutoScaleConnection
from awslimitchecker.services.autoscaling import _AutoscalingService


class Test_AutoscalingService(object):

    pb = 'awslimitchecker.services.autoscaling._AutoscalingService'

    def test_init(self):
        """test __init__()"""
        cls = _AutoscalingService(21, 43)
        assert cls.service_name == 'AutoScaling'
        assert cls.conn is None
        assert cls.warning_threshold == 21
        assert cls.critical_threshold == 43

    def test_connect(self):
        """test connect()"""
        mock_conn = Mock()
        cls = _AutoscalingService(21, 43)
        with patch('awslimitchecker.services.autoscaling.boto.connect_'
                   'autoscale') as mock_autoscaling:
            mock_autoscaling.return_value = mock_conn
            cls.connect()
        assert mock_autoscaling.mock_calls == [call()]
        assert mock_conn.mock_calls == []

    def test_connect_again(self):
        """make sure we re-use the connection"""
        mock_conn = Mock()
        cls = _AutoscalingService(21, 43)
        cls.conn = mock_conn
        with patch('awslimitchecker.services.autoscaling.boto.connect_'
                   'autoscale') as mock_autoscaling:
            mock_autoscaling.return_value = mock_conn
            cls.connect()
        assert mock_autoscaling.mock_calls == []
        assert mock_conn.mock_calls == []

    def test_get_limits(self):
        cls = _AutoscalingService(21, 43)
        cls.limits = {}
        res = cls.get_limits()
        assert sorted(res.keys()) == sorted([
            'Auto Scaling groups',
            'Launch configurations',
        ])
        for name, limit in res.items():
            assert limit.service == cls
            assert limit.def_warning_threshold == 21
            assert limit.def_critical_threshold == 43

    def test_get_limits_again(self):
        """test that existing limits dict is returned on subsequent calls"""
        mock_limits = Mock()
        cls = _AutoscalingService(21, 43)
        cls.limits = mock_limits
        res = cls.get_limits()
        assert res == mock_limits

    def test_find_usage(self):
        mock_conn = Mock(spec_set=AutoScaleConnection)
        mock_conn.get_all_groups.return_value = [1, 2, 3]
        mock_conn.get_all_launch_configurations.return_value = [1, 2]

        with patch('%s.connect' % self.pb) as mock_connect:
            cls = _AutoscalingService(21, 43)
            cls.conn = mock_conn
            assert cls._have_usage is False
            cls.find_usage()
        assert mock_connect.mock_calls == [call()]
        assert cls._have_usage is True
        asgs = sorted(cls.limits['Auto Scaling groups'].get_current_usage())
        assert len(asgs) == 1
        assert asgs[0].get_value() == 3
        lcs = sorted(cls.limits['Launch configurations'].get_current_usage())
        assert len(lcs) == 1
        assert lcs[0].get_value() == 2

    def test_required_iam_permissions(self):
        cls = _AutoscalingService(21, 43)
        assert cls.required_iam_permissions() == [
            'autoscaling:DescribeAutoScalingGroups',
            'autoscaling:DescribeLaunchConfigurations',
        ]
